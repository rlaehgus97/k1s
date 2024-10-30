import subprocess
import time
from notify import line_notify, discord_notify, notifies
from collections import deque

# 설정 변수
CPU_THRESHOLD_MAX = 0.8  # CPU 사용률 80% 초과 시 스케일 아웃
CPU_THRESHOLD_MIN = 0.2  # CPU 사용률 20% 미만 시 스케일 인
MONITOR_DURATION = 60 # 60초 동안 CPU 사용률 지켜보고 스케일 인/아웃
SCALE_INCREMENT = 1  # 스케일 아웃 시 추가할 컨테이너 수
CONTAINER_PREFIX = "rlaehgus-blog"  # 새로 생성될 컨테이너 이름의 접두사
IMAGE_NAME = "rlaehgus-blog"  # 컨테이너 생성시 쓸 이미지
ENV_VARS = {"VIRTUAL_HOST": "localhost", "VIRTUAL_PORT": "80"}  # 환경 변수
MIN_REPLICAS = 1 # 최소로 유지할 컨테이너 수
BASE_PORT = 8950 # blog 시작 포트 번호

# 각 컨테이너 cpu 사용률 기록 저장
cpu_usage_history = {}

def get_running_containers(prefix):
    """rlaehgus-blog로 시작하는 모든 실행 중인 컨테이너 ID 리스트를 반환합니다."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={prefix}", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            check=True # 명령어 실패할 경우 자동으로 예외 발생시킴
        )
        container_ids = result.stdout.strip().splitlines()
        return container_ids
    except subprocess.CalledProcessError as e:
        error_message = f"❗ 실행되고 있는 컨테이너들의 목록을 가져오는데 실패했습니다: {e}"
        print(error_message)
        notifies(error_message)
        return []

def get_container_cpu_usage(container_id):
    """주어진 컨테이너의 CPU 사용률을 반환합니다."""
    try:
        result = subprocess.run(
            ["docker", "stats", container_id, "--no-stream", "--format", "{{.CPUPerc}}"],
            capture_output=True,
            text=True,
            check=True # 이것이 없으면 예외발생 X, 결과를 result.stdout으로 확인만
        )
        # CPU 사용률에서 % 제거 후 실수로 변환
        cpu_usage_str = result.stdout.strip().replace('%', '')
        cpu_usage = float(cpu_usage_str) if cpu_usage_str else 0.0
        return cpu_usage
    except subprocess.CalledProcessError as e:
        error_message = f"❗ 컨테이너 {container_id}의 CPU 사용률을 얻는데 실패하였습니다: {e}"
        print(error_message)
        notifies(error_message)
        return 0.0
    
def scale_out(current_count):
    """스케일 아웃하여 새 컨테이너를 추가합니다."""
    target_count = current_count + SCALE_INCREMENT
    print(f"Scaling out: 총 {target_count}개의 컨테이너를 생성하기 위해{SCALE_INCREMENT}개의 컨테이너를 추가합니다...")

    for i in range(SCALE_INCREMENT):
        new_container_name = f"{CONTAINER_PREFIX}-{current_count + i + 1}"
        port_mapping = f"{BASE_PORT + current_count + i}:80"  # 순차적으로 포트 할당
        #port_mapping = f"80"
        env_options = [f"-e {key}={value}" for key, value in ENV_VARS.items()]
        
        try:
            subprocess.run([
                "docker", "run", "-d",
                "--name", new_container_name,
                "-p", port_mapping,
                *env_options,
                IMAGE_NAME
            ], check=True)
            success_message = f"✅ 컨테이너 {new_container_name}가 포트 {BASE_PORT + current_count + i}로 생성 성공!"
            print(success_message)
            notifies(success_message)        
        except subprocess.CalledProcessError as e:
            error_message = f"⚠️ 컨테이너 {new_container_name} 생성 실패: {e}"
            print(error_message)
            notifies(error_message) 
            return
        
    print(f"Scale out 프로세스 완료.")

def scale_in(current_count):
    """스케일 인하여 컨테이너 하나를 지웁니다."""
    # 최소 1개의 컨테이너는 살려야 함
    if current_count <=  MIN_REPLICAS:
        msg = f"최소 replica 개수: ({MIN_REPLICAS})에 도달했습니다; scale in 하지 않습니다."
        print(msg)
        notifies(msg)
        return
    
    container_to_remove = f"{CONTAINER_PREFIX}-{current_count}"
    print(f"Scaling in: 컨테이너 {container_to_remove}를 지웁니다...")

    try:
        subprocess.run(["docker", "rm", "-f", container_to_remove], check=True)
        success_message = f"✅ 컨테이너 {container_to_remove} 성공적으로 제거되었습니다."
        print(success_message)
        notifies(success_message)
    except subprocess.CalledProcessError as e:
        error_message = f"⚠️ 컨테이너 {container_to_remove}의 제거에 실패하였습니다: {e}"
        print(error_message)
        notifies(error_message)

def monitor_and_scale():
    """컨테이너 CPU 사용량을 모니터링하고, 임계치에 따라 스케일 아웃/인을 합니다."""
    while True:
        container_ids = get_running_containers(CONTAINER_PREFIX)
        current_count = len(container_ids)

        if current_count == 0:
            print("No containers running.")
            notifies("⚠️ No containers running.")
            return

        for container_id in container_ids:
            cpu_usage = get_container_cpu_usage(container_id)
            print(f"현재 컨테이너 {container_id}의 CPU 사용량: {cpu_usage:.2f}%")

            # 10초마다 컨테이너들의 각 CPU 사용량 기록
            if container_id not in cpu_usage_history:
                cpu_usage_history[container_id] = deque(maxlen=MONITOR_DURATION // 10)

            cpu_usage_history[container_id].append(cpu_usage)

            # 스케일 아웃: CPU 사용률이 upper 기준 1분이상이면 스케일 아웃
            """cpu_usage_history 1분간의 사용량 (6개)를 전부 기록했을 때"""
            if len(cpu_usage_history[container_id]) == cpu_usage_history[container_id].maxlen:
                """cpu_usage_history[container_id]안의 모든 usage가 threshold를 넘을때 만족"""
                if all(usage > CPU_THRESHOLD_MAX for usage in cpu_usage_history[container_id]):
                    message = f"🚨 컨테이너 {container_id}가 CPU 사용량 기준치 ({CPU_THRESHOLD_MAX}%)를 1분동안 넘었습니다. Scaling out 합니다..."
                    print(message)
                    notifies(message)
                    scale_out(current_count)
                    return
            
        # 스케일 인: 전체 컨테이너의 1분간 평균 CPU 사용률이 lower기준보다 낮을 경우
        avg_cpu_usage = sum([sum(cpu_usage_history[cid]) / len(cpu_usage_history[cid]) for cid in container_ids]) / current_count
        if avg_cpu_usage < CPU_THRESHOLD_MIN:
            message = f"평균 CPU 사용량 ({avg_cpu_usage:.2f}%)이 기준보다 ({CPU_THRESHOLD_MIN}%) 낮습니다. Scaling in 합니다..."
            print(message)
            notifies(message)
            scale_in(current_count)

        time.sleep(10)  # 10초 간격으로 모니터링

if __name__ == "__main__":
    monitor_and_scale()


