from ccs import FreeschemaQuery, DATAID, schema_query_listener, flatten_to_simple

class CCSSource():

    def __init__(
            self,
            entity_id = 0
    )-> None:
        self.entity_id = entity_id
        self.usage = None
    async def getTotalUsage(self):

        output = None
        if self.usage != None:
            output = self.usage
        else:

            print("this is the total usage")
            llmQuery = FreeschemaQuery(
                typeConnection="the_entity_s_llm_tracker",
                selectors=[            
                "the_llm_tracker_provider",
                "the_llm_tracker_model",
                "the_llm_tracker_cost",
                "the_llm_tracker_tokens"
                ]
            )

            query = FreeschemaQuery(
                conceptIds=[self.entity_id],
                name="top",
                freeschemaQueries= [llmQuery],
                outputFormat=DATAID,
                inpage=10,
                page=1
            )

            try:
                result = await schema_query_listener(query)
                print(f"\n--- Query Results ---")
                print(f"Data loaded: {result.isDataLoaded}")
                print(f"Main compositions: {len(result.mainCompositionIds)}")
                print(f"Concept IDs: {len(result.conceptIds)}")
                print(f"Linkers: {len(result.linkers)}")

                if result.data:
                    output = result.data
                    out = flatten_to_simple(result.data)
                    output = out
                    self.usage = out

                else:
                    print("\nNo data returned (this may be expected if no items exist)")
            except Exception as e:
                print(f"Query error: {e}")
                import traceback
                traceback.print_exc()

        return output
    
    async def count_cost(self):
        output = await self.getTotalUsage()
        sum = 0
        out = output[0]
        dee = out['entity_s_llm_tracker']

        for data in dee:
            sum = sum +  float(data.get("llm_tracker_cost", "0"))
        return sum
    
    async def count_total_tokens(self):
        output = await self.getTotalUsage()
        sum = 0
        out = output[0]
        dee = out['entity_s_llm_tracker']

        for data in dee:
            sum = sum +  float(data.get("llm_tracker_tokens", "0"))
        return sum