import { Route, Routes } from "react-router-dom";

import CourseDetailPage from "../pages/CourseDetailPage.jsx";
import CoursesPage from "../pages/CoursesPage.jsx";
import HealthPage from "../pages/HealthPage.jsx";
import HomePage from "../pages/HomePage.jsx";
import NotFoundPage from "../pages/NotFoundPage.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/courses" element={<CoursesPage />} />
      <Route path="/courses/:id" element={<CourseDetailPage />} />
      <Route path="/health" element={<HealthPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
