package main

import (
	"bytes"
	"context"
	"fmt"
	"github.com/gin-contrib/cors"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
	"github.com/gin-gonic/gin"
	"github.com/phpdave11/gofpdf"
)

type customClaims struct {
	Username    string `json:"given_name"`
	RealmAccess struct {
		Roles []string `json:"roles"`
	} `json:"realm_access"`
}

func init() {
	log.SetFlags(log.LstdFlags | log.Llongfile)
}

func main() {
	// контекст необходим библиотеке go‑oidc
	ctx := context.Background()

	realmURL := os.Getenv("KEYCLOAK_URL") + "/realms/" + os.Getenv("KEYCLOAK_REALM")
	log.Println("realmURL:", realmURL)

	// чего то у меня тут не работает через depends_on по докеру
	// просто тупо поставим паузу, чтобы Keycloak успел запуститься
	time.Sleep(3 * time.Second)
	// инициализируем OIDC‑провайдера
	provider, err := oidc.NewProvider(ctx, realmURL)
	if err != nil {
		log.Fatalf("не удалось инициализировать OIDC‑провайдера: %v", err)
	}

	verifier := provider.Verifier(&oidc.Config{
		SkipClientIDCheck: true,
		ClientID:          "reports-api"},
	)

	// основной маршрутизатор
	router := gin.Default()

	// мы чисто для теста разрешаем всем ходить
	// так бы наверное я завел через прокси nginx и там cors не нужен
	router.Use(cors.New(cors.Config{
		AllowAllOrigins:  true,
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"},
		AllowHeaders:     []string{"*"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	// защищённый маршрут
	router.GET("/reports", auth(verifier), reports)

	// запускаем HTTP‑сервер
	if err := router.Run(":8000"); err != nil {
		log.Fatalf("сервер завершился с ошибкой: %v", err)
	}
}

func auth(v *oidc.IDTokenVerifier) gin.HandlerFunc {
	return func(c *gin.Context) {
		// извлекаем JWT из заголовка Authorization: Bearer <token>
		authHeader := c.GetHeader("Authorization")
		if !strings.HasPrefix(authHeader, "Bearer ") {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "отсутствует заголовок Authorization"})
			return
		}

		rawToken := strings.TrimPrefix(authHeader, "Bearer ")

		// проверяем подпись, срок действия и аудиторию
		idToken, err := v.Verify(c.Request.Context(), rawToken)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "невалидный токен", "details": err.Error()})
			return
		}

		// раскодируем кастомные claims для проверки роли
		var claims customClaims
		if err := idToken.Claims(&claims); err != nil {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": "не удалось разобрать claims", "details": err.Error()})
			return
		}

		// проверяем присутствие роли
		hasRole := false
		for _, r := range claims.RealmAccess.Roles {
			if r == "prothetic_user" {
				hasRole = true
				break
			}
		}
		if !hasRole {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "недостаточно прав"})
			return
		}

		// запишим в контекст имя пользователя
		c.Set("name", claims.Username)
		c.Next()
	}
}

func reports(c *gin.Context) {
	userName, _ := c.Get("name")

	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetFont("Arial", "", 16)
	pdf.AddPage()
	pdf.Cell(40, 10, fmt.Sprintf("Raport for %s", userName))

	var buf bytes.Buffer
	if err := pdf.Output(&buf); err != nil {
		c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": "не удалось создать PDF"})
		return
	}

	fileName := fmt.Sprintf("report_%s.pdf", userName)
	c.Header("Content-Type", "application/pdf")
	c.Header("Content-Disposition", "attachment; filename=\""+fileName+"\"")
	c.Data(http.StatusOK, "application/pdf", buf.Bytes())
}
