// The one query of the app: Aurora Sales by year, month, region, category and product (about a thousand rows).
import query from './aurora-cube.dax?raw';

const connection = 'aurora'; // the connector name in rayfin/rayfin.yml

export function auroraCube() {
  return { connection, query };
}
