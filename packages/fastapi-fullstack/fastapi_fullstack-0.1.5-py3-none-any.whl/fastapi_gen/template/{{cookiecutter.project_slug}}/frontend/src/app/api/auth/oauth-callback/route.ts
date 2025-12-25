{%- if cookiecutter.enable_oauth %}
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const { accessToken, refreshToken } = await request.json();

    if (!accessToken || !refreshToken) {
      return NextResponse.json(
        { error: "Missing tokens" },
        { status: 400 }
      );
    }

    const cookieStore = await cookies();

    // Set access token cookie
    cookieStore.set("access_token", accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24, // 24 hours
      path: "/",
    });

    // Set refresh token cookie
    cookieStore.set("refresh_token", refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: "/",
    });

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json(
      { error: "Failed to process OAuth callback" },
      { status: 500 }
    );
  }
}
{%- else %}
import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({ error: "OAuth not enabled" }, { status: 404 });
}
{%- endif %}
