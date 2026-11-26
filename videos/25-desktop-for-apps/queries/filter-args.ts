import type { ManagedQueryFactoryParams } from "@microsoft/fabric-interaction-manager";

export interface SalesFilterParams {
    year?: number | null;
    region?: string | null;
    category?: string | null;
}

export type SalesQueryParams = ManagedQueryFactoryParams & SalesFilterParams;

function escapeDaxString(value: string): string {
    return value.replace(/"/g, '""');
}

export function salesFilterArguments(params: SalesFilterParams): string[] {
    const filters: string[] = [];
    if (params.year != null) {
        filters.push(`TREATAS({${params.year}}, 'Date'[Year])`);
    }
    if (params.region) {
        filters.push(`TREATAS({"${escapeDaxString(params.region)}"}, 'Regions'[Region])`);
    }
    if (params.category) {
        filters.push(`TREATAS({"${escapeDaxString(params.category)}"}, 'Products'[Category])`);
    }
    return filters;
}
