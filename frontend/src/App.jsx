import AppRoutes from "./routes/AppRoutes.jsx";
import Layout from "./components/Layout.jsx";
import RoleSelectionPage from "./pages/RoleSelectionPage.jsx";
import { useAuth } from "./context/AuthContext.jsx";

export default function App() {
  const { needsRoleSelection } = useAuth();

  return (
    <Layout>
      {needsRoleSelection ? <RoleSelectionPage /> : <AppRoutes />}
    </Layout>
  );
}
