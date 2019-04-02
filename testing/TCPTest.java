import java.net.*;
import java.io.*;

public class TCPTest {
    public static void main(String[] args) {
        String hostName = args[0];
        int portNumber = Integer.parseInt(args[1]);

        try {
                Socket echoSocket = new Socket(hostName, portNumber);
                System.out.println("Success: Connected");
        }
        catch ( IOException e ) {
            System.err.println("Failed: Did not connect");
            e.printStackTrace();
        }
    }
}
