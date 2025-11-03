package reporter

import (
	"context"
	"fmt"
	"log"
	"time"

	"bionicpro/internal/config"
	"github.com/jmoiron/sqlx"

	_ "github.com/ClickHouse/clickhouse-go/v2"
)

type Reporter struct {
	conn *sqlx.DB
}

type UserReport struct {
	ProsthesisID           int64     `db:"prosthesis_id" json:"prosthesis_id"`
	Username               string    `db:"username" json:"username"`
	Email                  string    `db:"email" json:"email"`
	SensorType             string    `db:"sensor_type" json:"sensor_type"`
	SensorName             string    `db:"sensor_name" json:"sensor_name"`
	ForceNewtonsAVG        int       `db:"force_newtons_avg" json:"force_newtons_avg"`
	BatteryLevelPercentAVG int       `db:"battery_level_percent_avg" json:"battery_level_percent_avg"`
	CreatedAt              time.Time `db:"created_at" json:"created_at"`
}

func NewReporter(config config.ReporterConfig) *Reporter {
	connStr := fmt.Sprintf(
		"clickhouse://%s:%s@%s/%s?dial_timeout=2s&read_timeout=5s",
		config.Username, config.Password, config.Address, config.Database,
	)

	db, err := sqlx.Open("clickhouse", connStr)
	if err != nil {
		log.Fatalf("failed to open clickhouse connection: %v", err)
	}

	ctx := context.Background()
	if err := db.PingContext(ctx); err != nil {
		log.Fatalf("failed to ping clickhouse: %v", err)
	}

	return &Reporter{
		conn: db,
	}
}

func (r *Reporter) Close() {
	_ = r.conn.Close()
}

func (r *Reporter) GenReport(ctx context.Context, user string) ([]UserReport, error) {
	query := `
		SELECT  prosthesis_id,
				email,
				sensor_type,
    			sensor_name,
    			force_newtons_avg,
				battery_level_percent_avg,
				created_at
		FROM reports
		WHERE username = ?
	`

	var userReports []UserReport
	err := r.conn.SelectContext(ctx, &userReports, query, user)
	if err != nil {
		return nil, err
	}

	return userReports, nil
}
