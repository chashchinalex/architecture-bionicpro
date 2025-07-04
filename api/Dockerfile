FROM golang:1.24-alpine AS build
WORKDIR /src
COPY . .
RUN go mod download
RUN CGO_ENABLED=0 go build -o /out/reports-api .

FROM scratch
ENV KEYCLOAK_URL=http://localhost:8080
ENV KEYCLOAK_REALM=reports-realm
COPY --from=build /out/reports-api /reports-api
ENTRYPOINT ["/reports-api"]
