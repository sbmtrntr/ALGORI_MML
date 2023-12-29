import { StatusCodes } from 'http-status-codes';

import { BaseError } from './base.error';
import { BaseOptionError } from '../../../commons';

export class TooManyRequestsError extends BaseError {
  constructor(options: BaseOptionError = {}) {
    super({
      code: options.code,
      status: StatusCodes.TOO_MANY_REQUESTS,
      message: options.message,
      error: options.error,
    });
  }
}
