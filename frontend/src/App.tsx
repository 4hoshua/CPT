import { useState } from "react";
import { isLoggedIn } from "./auth";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  return loggedIn ? (
    <Dashboard onLogout={() => setLoggedIn(false)} />
  ) : (
    <Login onLogin={() => setLoggedIn(true)} />
  );
}
