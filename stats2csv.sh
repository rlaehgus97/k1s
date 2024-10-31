#!/bin/bash

# 시작 시간 타임스탬프 (형식: YYYYMMDDHHMMSS)
timestamp=$(date "+%Y%m%d%H%M%S")

# CSV 파일명과 경로 설정 (타임스탬프 포함)
output_file="docker_stats_${timestamp}.csv"

# CSV 헤더 작성
echo "Timestamp,Name,CPU,Memory" > $output_file

# 10초마다 docker stats 실행
while true; do
  # 현재 시간 저장 (형식: YYYY-MM-DD HH:MM:SS)
  timestamp=$(date "+%Y-%m-%d %H:%M:%S")

  # docker stats를 실행하여 1회 측정 후 결과를 파싱
  docker stats --no-stream --format "$timestamp,{{.Name}},{{.CPUPerc}},{{.MemPerc}}" >> $output_file

  # 10초 대기
  sleep 10
done
