"use client";

export default function LogoutButton() {
  const handleLogout = async () => {
    await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/auth/logout`,
      { method: "POST", credentials: "include" }
    );
    window.location.href = "/login";
  };

  return (
    <button
      onClick={handleLogout}
      className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
    >
      Logg ut
    </button>
  );
}
