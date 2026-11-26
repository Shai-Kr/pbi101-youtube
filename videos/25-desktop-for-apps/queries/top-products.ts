import baseQuery from "./top-products.dax?raw";
import { insertInteractionFilters } from "@/lib/query-factory";
import type { ColumnMetadataMap } from "@/lib/to-data-table";
import { salesFilterArguments, type SalesQueryParams } from "./filter-args";

export const connection = "aurora-sales";

export const columnMetadata: ColumnMetadataMap = {
    "Products[Product]": { name: "Product", displayName: "Product" },
    "[Revenue]": { name: "Revenue", displayName: "Revenue", format: "$#,0" },
    "[Margin %]": { name: "Margin", displayName: "Margin", format: "0.0%" },
};

export function topProducts(
    { interactionFilters = [], ...filters }: SalesQueryParams = {},
) {
    return {
        connection,
        query: insertInteractionFilters(baseQuery, [...salesFilterArguments(filters), ...interactionFilters], "/*__FILTER_ARGUMENTS__*/", "beforeMeasures"),
        columnMetadata,
    };
}
