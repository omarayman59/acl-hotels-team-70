import { type LucideIcon as LucideIconType } from "lucide-react";

export type NavigationUserType = {
  name: string;
  logo: string;
};

export type NavigationItemType = {
  id: string;
  title: string;
  icon: LucideIconType;
  action: () => void;
};
