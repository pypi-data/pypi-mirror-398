#!/bin/bash
# Import tasks extracted from 2025-12-24 voice journal

# P0 - Urgent
todo add "Define 35 thesis criteria for Studio 3 - EBITDA 5-10M, existing market, AI+marketing fit" -p p0 -P studio3 -t strategy,criteria
todo add "Complete the financial model" -p p0 -P finance -t model,urgent
todo add "Create VSL V1 draft" -p p0 -P marketing -t vsl,v1
todo add "Create Facebook ads V1 - 1 ad minimum" -p p0 -P marketing -t facebook,ads,v1
todo add "Check on deal status - did money come through" -p p0 -P deals -t followup,money

# P1 - High priority
todo add "Source 10-15 business ideas from Amazon sellers" -p p1 -P studio3 -t research,amazon
todo add "Source 10-15 business ideas from Etsy sellers" -p p1 -P studio3 -t research,etsy
todo add "Source 10-15 business ideas from eBay sellers" -p p1 -P studio3 -t research,ebay
todo add "Contact Marie if deal closed" -p p1 -P deals -t followup,contact
todo add "Book psychiatrist appointment - target Dec 29" -p p1 -P health -t medical,appointment
todo add "Get Vyvanse prescription - 6 months supply" -p p1 -P health -t medication,prescription
todo add "Get missing papers/documentation in Montreal" -p p1 -P admin -t documents,canada
todo add "Build copy chief sub-agent - John Carlton persona" -p p1 -P ai-system -t subagent,copywriting
todo add "Build copy chief sub-agent - Gary Halbert persona" -p p1 -P ai-system -t subagent,copywriting
todo add "Create customer avatar sub-agent with Reddit/Amazon data" -p p1 -P ai-system -t subagent,avatar
todo add "Build Meta compliance QA sub-agent" -p p1 -P ai-system -t subagent,compliance,meta
todo add "Build FDA compliance QA sub-agent" -p p1 -P ai-system -t subagent,compliance,fda
todo add "Build pristine guardian sub-agent for claim verification" -p p1 -P ai-system -t subagent,qa,claims

# P2 - Normal priority
todo add "Transcribe all voice recordings to text" -p p2 -P admin -t transcription,journal
todo add "Learn Indian Devdan teachings - 1 week implementation" -p p2 -P learning -t education,implementation
todo add "Build copy chief sub-agent - Gary Bencivenga persona" -p p2 -P ai-system -t subagent,copywriting
todo add "Build proof copywriter sub-agent with testimonial library" -p p2 -P ai-system -t subagent,proof
todo add "Set up 4 Cloud Code accounts across terminals" -p p2 -P ai-system -t infrastructure,accounts
todo add "Create cron job system for autonomous plan execution" -p p2 -P ai-system -t automation,cron
todo add "Build 10 racing lanes for parallel agent execution" -p p2 -P ai-system -t infrastructure,parallel

echo "Imported 25 tasks from voice journal"
todo list
