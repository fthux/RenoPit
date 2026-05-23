import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import LandingPage from './pages/LandingPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectPage from './pages/ProjectPage'
import AnalysisPage from './pages/AnalysisPage'
import ReportPage from './pages/ReportPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<Layout />}>
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/project/:id" element={<ProjectPage />} />
        <Route path="/project/:id/analysis" element={<AnalysisPage />} />
        <Route path="/project/:id/report" element={<ReportPage />} />
      </Route>
    </Routes>
  )
}
