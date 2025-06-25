FROM node:18 AS web-builder

WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web .
RUN npm run build

# Python bot runtime
FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot ./bot

# Copy web build
COPY --from=web-builder /app/web/.next ./.next
COPY --from=web-builder /app/web/package.json ./package.json

# Copy Vercel config
COPY vercel.json .
COPY next.config.js .

# Expose port
EXPOSE 3000

# Start bot and web server
CMD python bot/main.py & cd /app && npm start