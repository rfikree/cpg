import java.net.*;
import java.io.*;

public class URLReader {
	public static void main(String[] args) {
		String URL = "https://lhappsqa.dmtispatial.com/filewebservice/fileservice.wsdl";
		URL myURL = null;
		URLConnection urlConn = null;
		
		if (  args.length > 0 ) {
			URL = args[0];
		}
		System.out.println("URL: " + URL);
		
		
		try {
			myURL = new URL(URL);
			
		} catch (MalformedURLException e) {
			System.out.println("Malformed URL: " + URL);
			e.printStackTrace();
			
		}
		
		try {
			urlConn = myURL.openConnection();	
		} catch ( IOException e ) {
			System.out.println("Failed to open URL: " + URL);
			e.printStackTrace();			
		}

		try {
			BufferedReader in = new BufferedReader( new InputStreamReader( urlConn.getInputStream() ));

			String inputLine;
	        while ((inputLine = in.readLine()) != null) 
	            System.out.println(inputLine);
	        in.close();
		
		} catch ( IOException e ) {
			System.out.println("Failed reading URL: " + URL);
			e.printStackTrace();			
		}
	}
}
