package com.bionicpro.api

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class BionicProApiApplication

fun main(args: Array<String>) {
	runApplication<BionicProApiApplication>(*args)
}