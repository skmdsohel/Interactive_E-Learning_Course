import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App.jsx";
import { AppProvider } from "./context/AppContext.jsx";
import { VideoPlayerProvider } from "./context/VideoPlayerContext.jsx";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AppProvider>
        <VideoPlayerProvider>
          <App />
        </VideoPlayerProvider>
      </AppProvider>
    </BrowserRouter>
  </StrictMode>
);
