package com.bionicpro.api.service

import com.bionicpro.api.model.Movement
import com.bionicpro.api.model.ReportResponse
import com.bionicpro.api.model.ReportRow
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import kotlin.random.Random

@Service
class ReportService {

    fun getReport(): ReportResponse {
        val rows = (1..30).map {
            ReportRow(
                date = LocalDateTime.now(),
                movement = Movement.entries.random(),
                signal  = Random.nextInt(0, 100),
                battery = Random.nextInt(5, 100)
            )
        }
        return ReportResponse(rows)
    }
}