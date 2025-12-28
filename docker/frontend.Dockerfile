FROM node:20-alpine as development

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host"]

FROM node:20-alpine as build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine as production

COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]