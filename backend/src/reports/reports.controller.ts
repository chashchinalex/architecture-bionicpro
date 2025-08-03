import { Controller, Get, SetMetadata, UseGuards, Req } from '@nestjs/common';
import { ReportsService } from './reports.service';
import { JwtAuthGuard } from 'src/auth/jwt-auth.guard';
import { RolesGuard } from 'src/auth/roles.guard';
import { Report } from './fake-reports.data';

@Controller('reports')
@UseGuards(JwtAuthGuard, RolesGuard)
export class ReportsController {
  constructor(private readonly reportsService: ReportsService) {}

  @Get()
  @SetMetadata('role', 'prothetic_user')
  getReports(@Req() req): Report[] {
    const userId = req.user?.preferred_username || req.user?.sub;

    if (!userId) {
      throw new Error('User ID not found in token');
    }

    return this.reportsService.getUserReports(userId);
  }
}
