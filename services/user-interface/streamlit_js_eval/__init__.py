
import streamlit.components.v1 as components

def get_geolocation():
    result = components.html(
        """
        <script>
        const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));
        const sendLocation = async () => {
            navigator.geolocation.getCurrentPosition(async (position) => {
                const coords = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                const streamlitEvent = new CustomEvent("streamlit:setComponentValue", {
                    detail: { value: coords },
                });
                document.dispatchEvent(streamlitEvent);
            });
            await sleep(500);
        };
        sendLocation();
        </script>
        """,
        height=0,
    )
    return result
