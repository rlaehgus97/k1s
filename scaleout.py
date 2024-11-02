import subprocess
import time

# 설정 변수
CPU_THRESHOLD_UPPER = 0.01  # CPU 사용률 9% 초과 시 스케일 아웃
CPU_THRESHOLD_LOWER = 0.002  # CPU 사용률 2% 초과 시 스케일 인
SCALE_INCREMENT = 1  # 스케일 아웃 시 추가할 컨테이너 수
CONTAINER_PREFIX = "rlaehgus-blog"  # 새로 생성도리 컨테이너 이름의 접두사
IMAGE_NAME = "rlaehgus-blog" 
ENV_VARS = {"VIRTUAL_HOST": "localhost", "VIRTUAL_PORT": "80"}  # 환경 변수

def get_running_containers(prefix):
    """지정된 접두사를 가진 모든 실행 중인 컨테이너 ID 리스트를 반환합니다."""
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={prefix}", "--format", "{{.ID}}"],
        capture_output=True,
        text=True
    )
    container_ids = result.stdout.strip().splitlines()
    return container_ids

def get_container_cpu_usage(container_id):
    """주어진 컨테이너의 CPU 사용률을 반환합니다."""
    result = subprocess.run(
        ["docker", "stats", container_id, "--no-stream", "--format", "{{.CPUPerc}}"],
        capture_output=True,
        text=True
    )
    # CPU 사용률에서 % 제거 후 실수로 변환
    cpu_usage_str = result.stdout.strip().replace('%', '')
    cpu_usage = float(cpu_usage_str) if cpu_usage_str else 0.0
    return cpu_usage

def scale_out(current_count):
    """스케일 아웃하여 새 컨테이너를 추가합니다."""
    target_count = current_count + SCALE_INCREMENT
    print(f"Scaling out: {target_count}개의 replica를 생성하기 위해{SCALE_INCREMENT}의 컨테이너를 추가합니다...")

    for i in range(SCALE_INCREMENT):
        new_container_name = f"{CONTAINER_PREFIX}-{current_count + i + 1}"
        #port_mapping = f"895{current_count + i + 1}:80"
        port_mapping = f"80"

        env_options = [f"-e {key}={value}" for key, value in ENV_VARS.items()]
        
        subprocess.run([
            "docker", "run", "-d",
            "--name", new_container_name,
            "-p", port_mapping,
            *env_options,
            IMAGE_NAME
        ])
    print(f"Scaled out to {target_count} replicas.")

def monitor_and_scale():
    """컨테이너 CPU 사용량을 모니터링하고, 임계치를 초과할 시 스케일 아웃합니다."""
    while True:
        container_ids = get_running_containers(CONTAINER_PREFIX)

        for container_id in container_ids:
            cpu_usage = get_container_cpu_usage(container_id)
            print(f"현재 컨테이너 {container_id} CPU usage: {cpu_usage:.2f}%")

            # 임계치 초과 시 스케일 아웃
            if cpu_usage > CPU_THRESHOLD_UPPER:
                print(f"컨테이너 {container_id}에서 CPU usage가 threshold ({CPU_THRESHOLD_UPPER}%)를 넘었습니다. Scaling out합니다...")
                scale_out(len(container_ids))
                return  # 스케일 아웃 후 루프 탈출
        
        time.sleep(10)  # 10초 간격으로 모니터링

if __name__ == "__main__":
    monitor_and_scale()


