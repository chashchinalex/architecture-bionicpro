import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getStartStatus(): string {
    return 'BionicPRO Reports API is running';
  }
}
