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
    
    // UPDATED MODEL: "gemini-1.5-flash" is the current standard.
    // If you want higher reasoning capability for "Why" questions, use "gemini-1.5-pro".
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    let contextPrompt = "";
    if (countryData) {
        // We summarize the data to keep the prompt clean
        const summaryData = {
          country: countryData.countryName,
          top_areas: countryData.topSubfields?.slice(0, 10), // Give it more top areas (10) for better context
          specializations: countryData.uniqueSubfields?.slice(0, 5),
          trends: "Available in context if needed" 
        };
        
        // --- THE KEY CHANGE IS HERE ---
        contextPrompt = `
        You are an expert Senior Research Analyst for a Global Science Dashboard. 
        
        You have access to REAL-TIME data for **${countryData.countryName}**:
        ${JSON.stringify(summaryData, null, 2)}
        
        Your Goal: Combine this specific data with your own broad knowledge of global economics, history, and policy.

        RULES FOR ANSWERING:
        1. **FACTS FIRST:** If the user asks "How many?" or "What is the top field?", YOU MUST use the provided JSON data. Do not make up numbers.
        2. **EXPLAIN THE "WHY":** If the user asks "Why is [Field] popular?", the JSON won't tell you. You must use your internal knowledge to explain. 
           - Example: If the data shows "Agriculture" is huge in Brazil, explain it's due to their massive soy/beef export economy and tropical climate.
           - Example: If "Molecular Biology" is #1 in the US, explain it's driven by the NIH budget, massive biotech hubs (Boston/SF), and pharmaceutical innovation.
        3. **BE INSIGHTFUL:** Don't just list numbers. Connect the dots. Mention government funding agencies (like NIH, NSF, Horizon Europe) if relevant to that country.
        `;
    } else {
        contextPrompt = "User has not selected a country. Politely ask them to click a country on the globe first.";
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
