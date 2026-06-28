import { Route, Routes } from "react-router-dom";

import CourseDetailPage from "../pages/CourseDetailPage.jsx";
import CoursesPage from "../pages/CoursesPage.jsx";
import HealthPage from "../pages/HealthPage.jsx";
import HomePage from "../pages/HomePage.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import NotFoundPage from "../pages/NotFoundPage.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/courses" element={<CoursesPage />} />
      <Route
        path="/courses/:id"
        element={
          <ProtectedRoute>
            <CourseDetailPage />
          </ProtectedRoute>
        }
      />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/health" element={<HealthPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
