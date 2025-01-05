FROM node:20.7.0-alpine as BUILD_IMAGE
WORKDIR /app/react-app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.21.6-alpine as PRODUCTION_IMAGE
COPY --from=BUILD_IMAGE /app/react-app/dist/ /usr/share/nginx/html
COPY env.sh /docker-entrypoint.d/env.sh
RUN chmod +x /docker-entrypoint.d/env.sh