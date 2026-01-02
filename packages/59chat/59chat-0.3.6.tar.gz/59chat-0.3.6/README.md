# Ephemeral Terminal Chat

Zero-trace terminal chat application with 59-second disappearing messages.

## Features

- Messages disappear after 59 seconds
- Zero trace - no history kept
- Fast terminal UI with Textual framework
- Mono font recommended (set in your terminal, e.g., JetBrains Mono)
- Supabase backend for real-time sync
- Share rooms with 6-character room codes
- Random nickname generation

## Setup

### 1. Supabase Setup

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to SQL Editor and run the `supabase_setup.sql` file
4. Get your project URL and anon key from Settings > API

### 2. Environment Variables

Copy `.env.example` to `.env` and add your Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python main.py
```

## Usage

- **Type a message** and press Enter to send
- **Ctrl+R** - Create new room
- **Ctrl+C** - Quit
- Share the **room code** with others to chat
- Messages auto-delete after 59 seconds

## How It Works

- Each room has a unique 6-character code
- Messages are stored in Supabase with timestamp
- Auto-cleanup deletes messages older than 59 seconds
- Terminal polls for new messages every second
- Zero-trace: no message history retained

## Terminal Share

Share your terminal with:
- tmate: `tmate`
- warp: Share session feature
- ssh: Allow remote connections
- Or just share the room code via any channel
