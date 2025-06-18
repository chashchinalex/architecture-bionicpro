FROM eclipse-temurin:21-jdk-jammy AS builder

WORKDIR /app
COPY . .
RUN ./mvnw -DskipTests clean package

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app

COPY --from=builder /app/target/app.jar app.jar

ENTRYPOINT ["java", "-jar", "app.jar"]