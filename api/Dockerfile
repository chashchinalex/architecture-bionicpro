FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build-env
WORKDIR /app
EXPOSE 8000

COPY ./src ./src
WORKDIR /app/src
RUN dotnet restore
RUN dotnet publish -c Release -o /publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS production-env
WORKDIR /app
COPY --from=build-env /publish .

ENTRYPOINT ["dotnet", "api.dll"]