package com.bionicpro.api.model

import java.time.LocalDateTime

data class ReportResponse(
    val rows: List<ReportRow>
)

data class ReportRow(
    val date: LocalDateTime,
    val movement: Movement,
    val signal: Int,
    val battery: Int
)

enum class Movement {
    OPEN,
    CLOSE,
    ROTATE,
    GRAB;
}