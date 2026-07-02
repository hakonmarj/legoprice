FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY backend-dotnet/src/Legoprice.Api/Legoprice.Api.csproj backend-dotnet/src/Legoprice.Api/
RUN dotnet restore backend-dotnet/src/Legoprice.Api/Legoprice.Api.csproj

COPY backend-dotnet/src/Legoprice.Api/ backend-dotnet/src/Legoprice.Api/
RUN dotnet publish backend-dotnet/src/Legoprice.Api/Legoprice.Api.csproj -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production
EXPOSE 8080

ENTRYPOINT ["dotnet", "Legoprice.Api.dll"]
