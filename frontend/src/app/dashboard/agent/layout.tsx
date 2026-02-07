import DashboardLayout from "@/components/DashboardLayout";

export default function AgentDashboardLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return <DashboardLayout>{children}</DashboardLayout>;
}
