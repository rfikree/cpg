import java.net.*;
import java.io.*;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import java.security.cert.X509Certificate;

//public class ConnectHttps {
public class URLReaderAny {
	public static void main(String[] args) throws Exception {
		/*
		 *  fix for
		 *    Exception in thread "main" javax.net.ssl.SSLHandshakeException:
		 *       sun.security.validator.ValidatorException:
		 *           PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException:
		 *               unable to find valid certification path to requested target
		 */
		TrustManager[] trustAllCerts = new TrustManager[] {
		   new X509TrustManager() {
			  public java.security.cert.X509Certificate[] getAcceptedIssuers() {
				return null;
			  }
	
			  public void checkClientTrusted(X509Certificate[] certs, String authType) {  }
	
			  public void checkServerTrusted(X509Certificate[] certs, String authType) {  }
	
		   }
		};
	
		SSLContext sc = SSLContext.getInstance("SSL");
		sc.init(null, trustAllCerts, new java.security.SecureRandom());
		HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());
	
		// Create all-trusting host name verifier
		HostnameVerifier allHostsValid = new HostnameVerifier() {
			public boolean verify(String hostname, SSLSession session) {
			  return true;
			}
		};
		// Install the all-trusting host verifier
		HttpsURLConnection.setDefaultHostnameVerifier(allHostsValid);
		/*
		 * end of the fix
		 */
	
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
		}
		
		try {
			urlConn = myURL.openConnection();
		}
		catch ( IOException e ) {
			System.err.println("Failed to open URL: " + URL);
			e.printStackTrace();
		}
	
		//URL url = new URL("https://securewebsite.com");
		//URLConnection con = url.openConnection();
		try {
			Reader reader = new InputStreamReader(urlConn.getInputStream());
			while (true) {
				int ch = reader.read();
				if (ch==-1) {
					break;
				}
				System.out.print((char)ch);
			}
		}
		catch ( IOException e ) {
			System.err.println("Failed reading URL: " + URL);
			e.printStackTrace();
		}
	}
}
