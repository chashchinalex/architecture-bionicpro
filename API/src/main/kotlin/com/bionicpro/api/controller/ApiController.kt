package com.bionicpro.api.controller

import com.bionicpro.api.model.ReportResponse
import com.bionicpro.api.service.ReportService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

@RestController
class ApiController(
    private val reportService: ReportService
) {

    @GetMapping("/reports")
    fun getReport(): ResponseEntity<ReportResponse> = ResponseEntity.ok(reportService.getReport())
}