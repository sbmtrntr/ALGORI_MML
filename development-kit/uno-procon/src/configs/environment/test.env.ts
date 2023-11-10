'use strict';

import * as path from 'path';
import { AppEnvironment } from '../../commons/interfaces';

export const ENV: AppEnvironment = {
  NAME: 'test',
  APP: {
    METHOD: 'http',
    HOST: '',
    PORT: 8083,
    TEST_PORT: 3000,
    IP: process.env['IP'] || '0.0.0.0',
  },
  SECURE: {
    JWT: {
      JWT_SECRET: `uno-localjwtauthenticate-##2020`,
      /*time expire token*/
      TOKEN_EXPIRE: 7 * 24 * 60 * 60, // 7 days
    },
  },
  DATABASE: {
    MONGODB: {
      USERNAME: '',
      PASSWORD: '',
      HOST: 'localhost',
      PORT: 27017,
      NAME: 'uno-test',
    },
    REDIS: {
      HOST: '127.0.0.1',
      PORT: 6379,
      DB: 4,
    },
  },
  IMAGE_STORE: {
    HOST: 'http://localhost:8083',
    ROOT: path.join(__dirname, '../../../../', 'public/buckets'),
    BUCKET: 'uno-test',
  },
};
