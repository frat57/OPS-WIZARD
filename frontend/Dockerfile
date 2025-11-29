FROM node:20-alpine AS base
WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json* ./
# If project doesn't have package-lock.json, npm ci fails. Use npm install to allow building
RUN npm install --omit=dev

COPY . .

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=base /app/ .

EXPOSE 3000
CMD ["npm", "run", "start"]
