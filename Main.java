import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

public class Main {
	String charset = "UTF-8";
	public static void main(String[] args) throws IOException {
		String urlString = 
			"https://api.nytimes.com/svc/search/v2/articlesearch.json";
		urlString += "?q=wind+power"
				+ "&api-key=61f3909960f048909642771cedab3b76"
				+ "&response-format=jsonp"
				+ "&callback=svc_search_v2_articlesearch";
		HttpURLConnection connection = (HttpURLConnection) new URL(urlString).openConnection();
		connection.setRequestMethod("GET");
		BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
		StringBuffer response = new StringBuffer();
		String line = in.readLine();
		while (line != null) {
			response.append(line);
			line = in.readLine();
		}
		JSONParser parser = new JSONParser();
		try {
			JSONObject obj = (JSONObject) parser.parse(response.toString());
			JSONObject resp = (JSONObject) obj.get("response");
			JSONArray docs = (JSONArray) resp.get("docs");
			JSONObject doc = (JSONObject) docs.get(0);
			
			// Loop through some arbitrary amount
			for (int i = 1; i < 10; i++) {
				doc = (JSONObject) docs.get(i);
				String abs =  (String) doc.get("abstract");
				String url = (String) doc.get("web_url");
				System.out.println("URL: " + url);
				
				// Send GET for url contents here
				
				// Find the HTML tag/class that contains the content
				// Looks like it's <p class="story-body-text story-content"
				
				// Use jtdiy to get the contents of this specific tag
				
				// Strip out links
				
				// Split contents on regex to get sentences e.g.: '. '
				
				// Map from article URL to set of sentences
				
			}
		} catch (ParseException e) {
			e.printStackTrace();
		}
	}
}
