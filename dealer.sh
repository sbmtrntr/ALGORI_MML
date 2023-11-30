#!/bin/bash
cd development-kit/uno-procon
docker-compose build
open http://localhost:8080/api/v1/admin/web
# if windows
# start http://localhost:8080/api/v1/admin/web
docker-compose up