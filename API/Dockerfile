FROM node:20.11.1-slim
# App directory
WORKDIR /app

# App dependencies
COPY package*.json ./
RUN npm install --production

# Copy app source code
COPY . .
RUN npm run build


# Start the app
ENTRYPOINT [ "npm", "run", "start:prod"]
