# VLR Scraper + Summarizer

## Overview
This project is a **web scraper and summarizer** for [VLR.gg](https://www.vlr.gg/), the leading community hub for competitive Valorant.  

The goal is to collect:
- **Match data**: Teams, scores, event, and date/time.  
- **Article data**: News posts and updates from the last 7 days.  

This information is exposed through a GraphQL API, making it easy to build downstream applications such as dashboards, chatbots, and automated news feeds.

---

## Current Features

### ✅ Match Scraping
- Traverses match index pages (`/matches`).
- Extracts:
  - Match ID  
  - Team A and Team B  
  - Final score (if available)  
  - Event name  
  - Date and time  

### ✅ Article Scraping
- Traverses homepage and `/news` pages.  
- Extracts:
  - Article ID  
  - Title  
  - URL  
  - Publication date  
- Filters results to only include **articles within the last 7 days**.  

### ✅ GraphQL API
- Provides structured access to scraped data.  
- Example queries:
  ```graphql
  query {
    lastWeekArticles {
      id
      title
      url
      publishedAt
    }
    lastWeekMatches {
      id
      teamA
      teamB
      scoreA
      scoreB
      event
      dateTime
    }
  }
