import { Injectable } from '@nestjs/common';
import { Report } from './fake-reports.data';
import { FAKE_REPORTS } from './fake-reports.data';

@Injectable()
export class ReportsService {
  getUserReports(userId: string): Report[] {
    return FAKE_REPORTS.filter((report) => report.userId === userId);
  }
}
