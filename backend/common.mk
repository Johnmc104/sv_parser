# 公共makefile配置

# 默认配置变量 (可以被覆盖)
PYTHON ?= python3
ROOT_DIR = $(shell pwd)
PID_FILE = $(ROOT_DIR)/log/$(APP_NAME).pid
LOG_FILE = $(ROOT_DIR)/log/$(APP_NAME).log

# 公共目标
.PHONY: help start stop restart status clean logs logs-follow install check_dir

help:
	@echo "Available commands:"
	@echo "  start       - Start $(APP_NAME) (run in background)"
	@echo "  stop        - Stop $(APP_NAME)"
	@echo "  restart     - Restart $(APP_NAME)"
	@echo "  status      - Check $(APP_NAME) status"
	@echo "  logs        - View $(APP_NAME) logs"
	@echo "  logs-follow - Follow $(APP_NAME) logs in real-time"
	@echo "  clean       - Clean PID and log files"
	@echo "  install     - Install dependencies"

check_dir:
	@if [ ! -d log ]; then \
	  echo "Log directory 'log' does not exist, creating..."; \
	  mkdir log; \
	else \
	  echo "Log directory 'log' exists."; \
	fi

# 启动应用
start: check_dir
	@if [ -f $(PID_FILE) ]; then \
	  if ps -p `cat $(PID_FILE)` > /dev/null 2>&1; then \
	    echo "$(APP_NAME) is already running (PID: `cat $(PID_FILE)`)"; \
	    exit 1; \
	  else \
	    echo "Removing invalid PID file"; \
	    rm -f $(PID_FILE); \
	  fi; \
	fi
	@echo "Starting $(APP_NAME)$(if $(PORT), on port $(PORT))..."
	@$(START_CMD) > $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE)
	@sleep 1
	@if [ -f $(PID_FILE) ]; then \
	  echo "$(APP_NAME) started (PID: `cat $(PID_FILE)`)"; \
	  $(if $(PORT),echo "Access URL: http://localhost:$(PORT)";) \
	  echo "Log file: $(LOG_FILE)"; \
	else \
	  echo "Failed to start $(APP_NAME)"; \
	  exit 1; \
	fi

# 停止应用
stop:
	@if [ ! -f $(PID_FILE) ]; then \
	  echo "PID file not found, $(APP_NAME) may not be running"; \
	  exit 1; \
	fi
	@PID=`cat $(PID_FILE)` && \
	if ps -p $$PID > /dev/null 2>&1; then \
	  echo "Stopping $(APP_NAME) (PID: $$PID)..."; \
	  pkill -P $$PID 2>/dev/null || true; \
	  kill $$PID 2>/dev/null || true; \
	  sleep 2; \
	  if ps -p $$PID > /dev/null 2>&1; then \
	    echo "Force stopping $(APP_NAME)..."; \
	    pkill -9 -P $$PID 2>/dev/null || true; \
	    kill -9 $$PID 2>/dev/null || true; \
	  fi; \
	  rm -f $(PID_FILE); \
	  echo "$(APP_NAME) stopped"; \
	else \
	  echo "Process not found, cleaning PID file"; \
	  rm -f $(PID_FILE); \
	fi
	@if [ -n "$(PORT)" ]; then \
	  PYTHON_PID=$$(lsof -ti:$(PORT) 2>/dev/null || true); \
	  if [ -n "$$PYTHON_PID" ]; then \
	    echo "Killing remaining Python process on port $(PORT) (PID: $$PYTHON_PID)"; \
	    kill -9 $$PYTHON_PID 2>/dev/null || true; \
	  fi; \
	fi

# 重启应用
restart: stop start

# 查看应用状态
status:
	@if [ ! -f $(PID_FILE) ]; then \
	  echo "$(APP_NAME) not running (PID file not found)"; \
	else \
	  PID=`cat $(PID_FILE)` && \
	  if ps -p $$PID > /dev/null 2>&1; then \
	    echo "$(APP_NAME) is running (PID: $$PID)"; \
	    $(if $(PORT),echo "Port: $(PORT)";) \
	    echo "Process information:"; \
	    ps -p $$PID -o pid,ppid,cmd,etime,pcpu,pmem; \
	  else \
	    echo "$(APP_NAME) not running (process not found)"; \
	    rm -f $(PID_FILE); \
	  fi; \
	fi

# 查看日志
logs:
	@if [ -f $(LOG_FILE) ]; then \
	  echo "Last 50 lines of logs:"; \
	  tail -50 $(LOG_FILE); \
	else \
	  echo "Log file not found"; \
	fi

# 实时查看日志
logs-follow:
	@if [ -f $(LOG_FILE) ]; then \
	  tail -f $(LOG_FILE); \
	else \
	  echo "Log file not found"; \
	fi

# 清理文件
clean:
	@echo "Cleaning PID and log files..."
	@rm -f $(PID_FILE) $(LOG_FILE)
	@echo "Cleanup completed"

# 安装依赖
install:
	@if [ -f requirements.txt ]; then \
	  $(PYTHON) -m pip install -r requirements.txt; \
	else \
	  echo "requirements.txt file not found"; \
	fi