export interface Report {
  reportId: string;
  userId: string;
  deviceId: string;
  period: string;
  averageUsageHours: number;
  signalStability: string;
  calibrationNeeded: boolean;
}

export const FAKE_REPORTS: Report[] = [
  {
    reportId: '1',
    userId: 'prothetic1',
    deviceId: 'prosthetic-001',
    period: '2025-03',
    averageUsageHours: 12.5,
    signalStability: '96%',
    calibrationNeeded: false,
  },
  {
    reportId: '2',
    userId: 'prothetic2',
    deviceId: 'prosthetic-002',
    period: '2025-03',
    averageUsageHours: 15.3,
    signalStability: '98%',
    calibrationNeeded: true,
  },
  {
    reportId: '3',
    userId: 'prothetic3',
    deviceId: 'prosthetic-003',
    period: '2025-03',
    averageUsageHours: 10.1,
    signalStability: '94%',
    calibrationNeeded: false,
  },
];