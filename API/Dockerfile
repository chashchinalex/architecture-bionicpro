FROM gradle:8.14.3-jdk21-corretto-al2023 AS build
WORKDIR /app
COPY . .
RUN gradle clean bootJar --no-daemon

FROM amazoncorretto:21-al2023
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java","-jar","/app/app.jar"]