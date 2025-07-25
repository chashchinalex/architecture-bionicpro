FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm config set ca=""
RUN npm set strict-ssl false
RUN npm i
COPY . .
EXPOSE 8000
CMD ["npm", "start"]