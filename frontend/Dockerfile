# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm config set registry https://registry.npmmirror.com
RUN npm install --no-audit --no-fund
COPY . ./
RUN npm run build
CMD cp -r build result_build
