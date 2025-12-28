/**
 * PM2 Configuration File
 *
 * This file configures two applications to be managed by PM2:
 * 1. fleet-manager-ui: Frontend served by bun.
 * 2. fleet-manager-api: Django backend served by Uvicorn (ASGI).
 *
 * Location: /home/apps/prod/ecosystem.config.js
 *
 * Usage:
 * 1) npm i -g pm2 serve   (serve only needed if you use it elsewhere)
 * 2) mkdir -p /home/apps/prod/logs
 * 3) From '/home/apps/prod': pm2 restart ecosystem.config.js
 * 4) pm2 logs
 * 5) pm2 stop all / pm2 delete all
 */
module.exports = {
    apps: [
    //   {
    //     name: "fleet-manager-ui",
    //     cwd: "/home/apps/prod/vyomos-fleet-manager-ui",
    //     script: "bun",
    //     args: "run start --port=8002",
    //     out_file: "./logs/ui-out.log",
    //     error_file: "./logs/ui-error.log",
    //     merge_logs: true,
    //     env: {
    //       NODE_ENV: "production",
    //       PORT: 8002,
    //     },
    //   },
      {
        name: "fleet-manager-ui",
        cwd: "/home/apps/prod/vyomos-fleet-manager-ui",
        script: "/root/.bun/bin/bun",
        args: "run start --port=8002",
        interpreter: "none",
        out_file: "/home/apps/prod/logs/ui-out.log",
        error_file: "/home/apps/prod/logs/ui-error.log",
        merge_logs: true,
        env: {
          NODE_ENV: "production",
          PORT: 8002,
        },
      },      
      {
        name: "fleet-manager-api",
        cwd: "/home/apps/prod/vyomos-fleet-manager-api",
        script: "/home/apps/venv/bin/uvicorn",
        args: [
          "vyom_fleet_manager.asgi:application",
          "--host",
          "0.0.0.0",
          "--port",
          "8001",
          "--workers",
          "3", // bump to 3 after it boots
          "--log-level",
          "info",
          "--access-log",
          "--proxy-headers",
          "--forwarded-allow-ips",
          "*",
          "--timeout-keep-alive",
          "300",
          "--timeout-graceful-shutdown",
          "30",
        ],
        interpreter: "none",
        instances: 1,
        autorestart: false, // true
        watch: false,
        max_memory_restart: "2G", // 1G
        out_file: "/home/apps/prod/logs/api-out.log",
        error_file: "/home/apps/prod/logs/api-error.log",
        merge_logs: true,
        log_date_format: "YYYY-MM-DD HH:mm Z",
        kill_timeout: 10000, // new field
        listen_timeout: 10000, // new field
        wait_ready: false, // new field
        env: {
          PYTHONUNBUFFERED: "1",
          DJANGO_LOG_LEVEL: "INFO",
          DJANGO_SETTINGS_MODULE: "vyom_fleet_manager.settings",
          PYTHONPATH:
            "/home/apps/prod/vyomos-fleet-manager-api/vyom_fleet_manager",
        },
      },
    ],
  };
  