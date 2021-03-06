import java.net.*;
import java.io.*;

public class URLReader {
	public static void main(String[] args) {
		String URL = "file:/etc/hosts";
		URL myURL = null;
		URLConnection urlConn = null;

		if (  args.length > 0 ) {
			URL = args[0];
		} else {
			System.out.println("URL: " + URL);
		}

		try {
			myURL = new URL(URL);
		}
		catch (MalformedURLException e) {
			System.err.println("Malformed URL: " + URL);
			e.printStackTrace();
			System.exit(-1);
		}

		try {
			urlConn = myURL.openConnection();
		}
		catch ( IOException e ) {
			System.err.println("Failed to open URL: " + URL);
			e.printStackTrace();
			System.exit(-1);
		}

		try {
			InputStream ins = urlConn.getInputStream();
			InputStreamReader insr = new InputStreamReader(ins);
			BufferedReader in = new BufferedReader(insr);

			String inputLine;
			while ((inputLine = in.readLine()) != null)
				System.out.println(inputLine);
			in.close();
			System.out.println(); // Ensure new line at end of content
		}
		catch ( IOException e ) {
			System.err.println("Failed reading URL: " + URL);
			e.printStackTrace();
			System.exit(-1);
		}
	}
}
