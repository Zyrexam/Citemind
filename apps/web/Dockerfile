FROM node:20-slim

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci

COPY apps/web/ ./

# NEXT_PUBLIC_* is inlined at build time, so this has to arrive as a build arg.
# Setting it in compose `environment:` is silently ignored.
ARG NEXT_PUBLIC_API_URL=http://localhost:8123
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]