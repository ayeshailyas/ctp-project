import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { message, countryData } = await req.json();
    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey) {
      return NextResponse.json({ error: "API Key missing" }, { status: 500 });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    let contextPrompt = "";
    if (countryData) {
        const summaryData = {
          country: countryData.countryName,
          top_areas: countryData.topSubfields?.slice(0, 5), 
          specializations: countryData.uniqueSubfields?.slice(0, 3),
        };
        
        contextPrompt = `
        You are an expert Senior Research Analyst.
        
        Data for **${countryData.countryName}**:
        ${JSON.stringify(summaryData)}
        
        YOUR GOAL: Combine this specific data with your own broad knowledge of global economics, history, geography, and policy.

        STRICT RULES:
        1. **KEEP IT SHORT:** Maximum 3-4 sentences or bullet points.
        2. **EXPLAIN THE "WHY":** If a field is popular, explain why using your external knowledge (e.g., "Agriculture is high due to the massive soy export economy" or "Medical research is driven by NIH funding").
        3. **NO FLUFF:** Start the answer immediately. Do not say "Based on the data".
        4. **BE INSIGHTFUL:** Mention specific funding agencies, historical reasons, or geographical factors if relevant.
        `;
    } else {
        contextPrompt = "User has not selected a country. Politely ask them to click a country on the globe first. Keep it very short.";
    }

    const result = await model.generateContent({
      contents: [
        {
          role: "user",
          parts: [
            { text: `System Context: ${contextPrompt}` },
            { text: `User Question: ${message}` }
          ]
        }
      ]
    });
    
    const response = result.response.text();
    return NextResponse.json({ response });

  } catch (error: any) {
    console.error("Chat Error:", error);
    return NextResponse.json({ 
      error: error.message || "Failed to process request" 
    }, { status: 500 });
  }
}
